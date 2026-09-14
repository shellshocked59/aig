"""Frozen full-match orchestration. Live mode requires an explicit bounded CLI scope."""
import argparse
from contextlib import contextmanager, ExitStack
from copy import deepcopy
import json
import os
from pathlib import Path
import time
from functools import lru_cache
from unittest.mock import patch

from aig.arena.case_study_contract import (ARMS, ID, DEFAULT_CONTRACT, LIMITS, read, sha,
                                         freeze, verify)
from aig.arena.case_study_metrics import match_metrics
from aig.arena.ai.benchmark_candidate import (CandidateObservation, CandidatePlan, EndTurnAction,
    base_observation, candidate_observation, SCHEMA_VERSION)
from aig.arena.ai.candidate_control import CandidateController
from aig.arena.ai.candidate_repair import OpenAIRepairCandidateProvider, NEW
from aig.arena.ai.heuristic_v2 import HeuristicArenaTurnProviderV2
from aig.arena.ai.observation import build_observation, OBSERVATION_V2
from aig.arena.ai.contracts import action_from_dict
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json, digest, from_snapshot, to_snapshot, command_from_dict
from aig.settings import OpenAISettings, load_settings

PROVIDER_FAILURES = {'repair_failed','transport_failure','timeout','timeout_failure','authentication_failure',
    'rate_limit','rate_limit_failure','provider_error','server_error','malformed_envelope','refusal',
    'empty_response','malformed_json','schema_validation','ap_budget','invalid_reference','invalid_ability',
    'connection_failure','api_failure','incomplete_response','provider_unavailable',
    'permission_denied','model_not_available','malformed_openai_response','api_error'}


class IntegrityError(RuntimeError):
    pass


class BudgetStop(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def write_new(path, value):
    """Exclusive, flushed evidence; a partial file after a crash fails closed."""
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as file:
        file.write(json.dumps(value,indent=2,ensure_ascii=True)+'\n')
        file.flush(); os.fsync(file.fileno())


def derived(path, value):
    """Only rebuildable aggregate views may be replaced."""
    path = Path(path)
    temp = path.with_suffix(path.suffix+'.tmp')
    with temp.open('w',encoding='utf-8') as file:
        file.write(json.dumps(value,indent=2)+'\n'); file.flush(); os.fsync(file.fileno())
    os.replace(temp,path)


@contextmanager
def exclusive(root):
    root = Path(root); root.mkdir(parents=True,exist_ok=True)
    with (root/'runner.lock').open('a+b') as file:
        file.seek(0); file.write(b'0'); file.flush(); file.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(file.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            yield
        finally:
            file.seek(0)
            if os.name == 'nt':
                msvcrt.locking(file.fileno(),msvcrt.LK_UNLCK,1)
            else:
                fcntl.flock(file.fileno(),fcntl.LOCK_UN)


@contextmanager
def no_network():
    with ExitStack() as stack:
        for target in ('socket.socket.connect','socket.socket.connect_ex','socket.create_connection',
                       'openai.resources.responses.responses.Responses.create'):
            stack.enter_context(patch(target,side_effect=AssertionError('offline: network forbidden')))
        yield


class Ledger:
    def __init__(self, root, limits=LIMITS, guard=lambda:None):
        self.root, self.limits, self.guard = Path(root), limits, guard
        self.rows = [read(p) for p in sorted((self.root/'requests').glob('*/reservation.json'))]
        for index,row in enumerate(self.rows,1):
            require(row['id']==index,'noncontiguous request ledger')

    def reserve(self, slot, turn):
        self.guard()
        arm, batch = slot['arm'],slot['batch']
        match = sum(r['match_id']==slot['match_id'] for r in self.rows)
        if match >= self.limits['per_match'][arm]:
            raise ArenaProviderError('request_ceiling')
        checks = [(len(self.rows),self.limits['global_requests']),
            (sum(r['arm']==arm for r in self.rows),self.limits['per_control'][arm]),
            (sum(r['batch']==batch for r in self.rows),self.limits['batch_requests']),
            (sum(r['batch']==batch and r['arm']==arm for r in self.rows),self.limits['per_batch_control'][arm])]
        if any(used>=limit for used,limit in checks):
            raise BudgetStop('cumulative request ceiling; preserve partial match and stop')
        row = dict(id=len(self.rows)+1,match_id=slot['match_id'],arm=arm,batch=batch,turn=turn)
        write_new(self.root/'requests'/f'{row["id"]:06d}'/'reservation.json',row)
        self.rows.append(row)
        return row['id']

    def receipt(self, request_id, value):
        write_new(self.root/'requests'/f'{request_id:06d}'/'receipt.json',value)


class JournalProvider(OpenAIRepairCandidateProvider):
    """Instrumentation around, not a change to, the frozen provider contract."""
    def __init__(self, settings, *, slot, ledger, fake=False, fake_policy=None):
        super().__init__(settings,step=slot['arm']=='stepwise',repair_version=NEW,
                         **({'client':object()} if fake else {}))
        self.slot,self.ledger,self.fake,self.fake_policy = slot,ledger,fake,fake_policy
        self.turn_ordinal = 0
        self.pending_id = None
        self.before_request = self.reserve

    def reserve(self):
        self.pending_id = self.ledger.reserve(self.slot,self.turn_ordinal)

    def request(self,messages,record):
        request_id = self.pending_id
        require(request_id is not None,'request without reservation')
        request_dir = self.ledger.root/'requests'/f'{request_id:06d}'
        write_new(request_dir/'payload.json',dict(instructions=self.system_prompt,input=messages,
            schema=self.output_schema(),configuration=self.configuration(),fake=self.fake))
        started = time.perf_counter()
        try:
            if self.fake:
                obs = CandidateObservation(messages[0]['content'].removeprefix('ArenaObservation:\n'))
                raw = self.fake_policy(obs,self.step) if self.fake_policy else fake_decision(obs,self.step)
                record['metrics'] = dict(input_tokens=10,output_tokens=5,total_tokens=15,
                                         cached_input_tokens=0,reasoning_tokens=0)
            else:
                raw = super().request(messages,record)
        except ArenaProviderError as error:
            self.ledger.receipt(request_id,dict(status='provider_error',error=error.category,
                seconds=time.perf_counter()-started,record=self._safe(record)))
            raise
        # Store structured response only. Invalid prose/hidden reasoning is never persisted.
        from aig.arena.ai.candidate_repair import structured
        obs=CandidateObservation(messages[0]['content'].removeprefix('ArenaObservation:\n'))
        safe_response=structured(raw,obs,self._secrets)
        self.ledger.receipt(request_id,dict(status='returned',seconds=time.perf_counter()-started,
            response_sha256=digest(raw),semantic_response=safe_response,record=self._safe(record)))
        record['ledger_id'] = request_id
        return raw


def fake_decision(observation,step):
    """Cheap deterministic legal-action fixture; no claim of Luna tactical behavior."""
    legal = observation.to_dict()['legal_actions']
    priorities = ('attack','finish','snipe','shield_bash','fireball','move','revive','heal','end_turn')
    action = min(legal,key=lambda a:(priorities.index(a['type']),canonical_json(a)))
    return canonical_json(dict(schema_version=SCHEMA_VERSION,actions=[action]))


@lru_cache(maxsize=4096)
def heuristic_plan(canonical):
    # Pure memoization of identical authoritative observations, useful in deterministic dry runs.
    from aig.arena.ai.observation import ArenaObservation
    return HeuristicArenaTurnProviderV2().create_turn_plan(ArenaObservation(canonical))


def heuristic_turn(sim):
    obs = build_observation(sim.state,version=OBSERVATION_V2)
    turn = sim.state.turn
    plan = heuristic_plan(obs.canonical)
    result = execute_arena_turn(sim.state,plan,execute_command=sim.execute).to_dict()
    require(result['invalid_action'] is None,'heuristic execution defect')
    return dict(provider='arena-heuristic-v2',observation=obs.to_dict(),observation_hash=obs.hash,
        plan=plan.to_dict(),execution=result,player_id=result['player_id'],turn=turn,
        ap_available=result['ap_available'],ap_executed=result['ap_spent'],ap_remaining=result['ap_unused'],
        stop_reason='TERMINAL' if sim.state.winner_player_id else 'CLEAN_PLAN_COMPLETE',provider_requests=0)


def seal(directory):
    files = {p.relative_to(directory).as_posix():sha(p) for p in sorted(directory.rglob('*.json'))
             if p.name!='seal.json'}
    write_new(directory/'seal.json',dict(files=files,sha256=digest(files)))


def check_seal(directory):
    saved = read(directory/'seal.json')
    actual = {p.relative_to(directory).as_posix():sha(p) for p in sorted(directory.rglob('*.json'))
              if p.name!='seal.json'}
    require(saved['files']==actual and saved['sha256']==digest(actual),'match artifact mutation')


def verify_match(directory, *, expected=None, contract=None):
    directory = Path(directory)
    if (directory/'seal.json').exists():
        check_seal(directory)
    manifest = read(directory/'manifest.json')
    external=read(directory/'request-ledger.json')
    for relative,hash_value in external['files'].items():
        require(sha(directory.parents[1]/relative)==hash_value,'request evidence mutation')
    if expected is not None:
        require(manifest['slot']==expected,'match schedule mismatch')
    if contract is not None:
        require(manifest['contract_sha256']==contract['sha256'],'match contract mismatch')
    full = read(directory/'command-trace.json')
    final = read(directory/'final-state.json')
    sim = replay(full)
    require(to_snapshot(sim.state)==final,'final replay mismatch')
    require(digest(full['initial_snapshot'])==manifest['slot']['initial_state_hash'],'initial state mismatch')
    turns, entries, cursor, ids = [], [], full['initial_snapshot'], []
    for ordinal,path in enumerate(sorted((directory/'turns').glob('*.json')),1):
        bundle = read(path); row, trace = bundle['turn'],bundle['trace']
        require(bundle['sha256']==digest({k:v for k,v in bundle.items() if k!='sha256'}),'turn checkpoint corruption')
        require(bundle['ordinal']==ordinal and trace['initial_snapshot']==cursor,'turn continuity')
        require(row['player_id']==cursor['active_player_id'],'turn player mismatch')
        part = replay(trace)
        require(to_snapshot(part.state)==bundle['final_state'],'turn replay mismatch')
        if row['player_id']==manifest['slot']['luna_side']:
            class Recorded:
                def __init__(self):
                    self.waves=iter(row['waves'])
                def create_turn_plan(self,obs):
                    wave=next(self.waves)
                    require(obs.to_dict()==wave['observation'] and obs.hash==wave['observation_hash'],'observation mismatch')
                    if wave['plan'] is None:
                        raise ArenaProviderError(wave['error_category'])
                    return CandidatePlan(tuple(EndTurnAction() if a=={'type':'end_turn'} else action_from_dict(a)
                                               for a in wave['plan']['actions']))
            detached = ArenaSimulation(from_snapshot(cursor))
            reproduced = CandidateController(Recorded(),mode=manifest['slot']['arm']).run_turn(detached)
            require(detached.trace()==trace,'control semantic replay mismatch')
            for key in ('stop_reason','ap_available','ap_executed','ap_remaining','replan_used','ap_recovered',
                        'second_invalidity','explicit_end_turn_decisions'):
                require(row[key]==reproduced[key],f'control telemetry mismatch: {key}')
            count = 0
            for wave in row['waves']:
                inf = wave['inference']
                require(not inf.get('fallback_used') and inf['requested_provider']=='openai','fallback/provider contamination')
                require(inf['actual_provider'] in (None,'openai'),'actual provider mismatch')
                require(inf['model']=='gpt-5.6-luna' and inf['repair_version']==NEW,'model/repair mismatch')
                require(inf['observation_hash']==wave['observation_hash'],'inference observation mismatch')
                require(inf['resulting_plan']==wave['plan'],'provider plan mismatch')
                if wave['plan'] is not None:
                    require(inf['actual_provider']=='openai','missing actual provider on accepted plan')
                if contract:
                    p=contract['payload']
                    require(inf['model_configuration']==p['configuration'] and inf['model_config_version']==p['profile'],
                            'model configuration mismatch')
                    require(inf['prompt_version']==('arena-step-prompt-v3' if manifest['slot']['arm']=='stepwise'
                                                    else 'arena-turn-prompt-v6'),'prompt mismatch')
                    require(inf['schema_version']==p['schema'] and inf['observation_version']==p['observation'],
                            'schema/observation binding mismatch')
                attempts = inf['attempts']
                for ai,attempt in enumerate(attempts):
                    request_dir=directory.parents[1]/'requests'/f'{attempt["ledger_id"]:06d}'
                    payload=read(request_dir/'payload.json');receipt=read(request_dir/'receipt.json')
                    require(payload['input'][0]['content']=='ArenaObservation:\n'+canonical_json(wave['observation']),
                            'request payload observation mismatch')
                    if contract:
                        require(payload['configuration']==p['configuration'] and payload['schema']==p['schemas'][manifest['slot']['arm']],
                                'request payload contract mismatch')
                        require(payload['instructions']==p['prompts'][inf['prompt_version']],'request prompt mismatch')
                    require(receipt['record'].get('metrics',{})==attempt.get('metrics',{}),'request metrics mismatch')
                    if ai:
                        from aig.arena.ai.candidate_repair import repair_messages
                        evidence=attempts[0]['rejected_decision']
                        expected_messages=repair_messages(CandidateObservation(canonical_json(wave['observation'])),
                            ArenaProviderError(attempts[0]['error_category']),evidence,NEW)
                        require(payload['input']==expected_messages,'repair request drift')
                    else:
                        require(len(payload['input'])==1,'unexpected initial context')
                count += len(attempts)
                ids.extend(a['ledger_id'] for a in attempts)
            require(count==row['provider_requests'],'turn request reconciliation')
        else:
            require(row['provider']=='arena-heuristic-v2' and row['provider_requests']==0,'heuristic binding')
            detached = ArenaSimulation(from_snapshot(cursor))
            from aig.arena.ai.contracts import ArenaTurnPlan
            plan = ArenaTurnPlan(tuple(action_from_dict(a) for a in row['plan']['actions']))
            obs=build_observation(detached.state,version=OBSERVATION_V2)
            require(row['observation']==obs.to_dict() and row['observation_hash']==obs.hash,'heuristic observation')
            require(heuristic_plan(obs.canonical)==plan,'heuristic deterministic policy mismatch')
            ex = execute_arena_turn(detached.state,plan,execute_command=detached.execute).to_dict()
            require(ex==row['execution'] and detached.trace()==trace,'heuristic replay mismatch')
        turns.append(row); entries.extend(trace['entries']); cursor=bundle['final_state']
    require(entries==full['entries'] and cursor==final,'full trace coverage')
    result=read(directory/'result.json')
    require(result['player_turns']==len(turns) and result['requests']==len(ids),'result accounting mismatch')
    require(result['metrics']==match_metrics(full,turns,manifest['slot']['luna_side']),'metric recomputation mismatch')
    require(result['engine_winner']==sim.state.winner_player_id,'engine winner mismatch')
    expected_cause=('CORE_DESTRUCTION' if any(c.hp==0 for c in sim.state.cores.values()) else 'TEAM_ELIMINATION') if sim.state.winner_player_id else (
        ('REQUEST_LIMIT' if turns[-1]['error_category']=='request_ceiling' else 'PROVIDER_FORFEIT')
        if turns and turns[-1].get('provider_failure') else 'TURN_LIMIT')
    require(result['terminal_cause']==expected_cause,'terminal taxonomy mismatch')
    if expected_cause=='TURN_LIMIT' and contract:
        require(len(turns)>=contract['payload']['limits']['player_turns'] or
                sim.state.turn>=contract['payload']['limits']['full_rounds'],'premature turn limit')
    expected_winner=manifest['slot']['heuristic_side'] if expected_cause=='PROVIDER_FORFEIT' else sim.state.winner_player_id
    require(result['winner']==expected_winner,'adjudicated winner mismatch')
    external=read(directory/'request-ledger.json')
    require(external['ids']==ids,'request ID coverage mismatch')
    root=directory.parents[1]
    for relative,hash_value in external['files'].items():
        require(sha(root/relative)==hash_value,'request evidence mutation')
    for ordinal,path in enumerate(sorted((directory/'turns').glob('*.json')),1):
        bundle=read(path)
        require(bundle['sha256']==digest({k:v for k,v in bundle.items() if k!='sha256'}),'checkpoint corruption')
        for rid in bundle['request_ids']:
            reservation=read(root/'requests'/f'{rid:06d}'/'reservation.json')
            require(reservation['match_id']==manifest['slot']['match_id'] and reservation['turn']==ordinal,
                    'request assigned to wrong match/turn')
            require(reservation['arm']==manifest['slot']['arm'] and reservation['batch']==manifest['slot']['batch'],
                    'request assigned to wrong control/batch')
    if contract:
        require(len(ids)<=contract['payload']['limits']['per_match'][manifest['slot']['arm']],'match request overrun')
    return dict(success=True,request_ids=ids,requests=len(ids),player_turns=len(turns),final_state_hash=digest(final))


def run_match(root,slot,contract,ledger,provider_factory,*,stop_after_turn=None):
    directory=Path(root)/'matches'/slot['match_id']
    p=contract['payload']; limits=p['limits']
    if not directory.exists():
        directory.mkdir(parents=True)
        write_new(directory/'manifest.json',dict(slot=slot,contract_sha256=contract['sha256'],
            mode=read(Path(root)/'benchmark-manifest.json')['mode']))
        write_new(directory/'initial-state.json',p['initial_state'])
    else:
        require(read(directory/'manifest.json')['slot']==slot,'partial match mismatch')
        require(read(directory/'manifest.json')['contract_sha256']==contract['sha256'],'partial contract mismatch')
        require(read(directory/'initial-state.json')==p['initial_state'],'partial initial-state mismatch')
    sim=ArenaSimulation(from_snapshot(p['initial_state'])); turns=[]; covered=[]
    for path in sorted((directory/'turns').glob('*.json')):
        bundle=read(path)
        require(bundle['sha256']==digest({k:v for k,v in bundle.items() if k!='sha256'}),'checkpoint corruption')
        for relative,value in bundle['request_files'].items():
            require(sha(Path(root)/relative)==value,'checkpoint request corruption')
        require(bundle['trace']['initial_snapshot']==to_snapshot(sim.state),'checkpoint discontinuity')
        for entry in bundle['trace']['entries']:
            require(sim.execute(command_from_dict(entry['command']))==entry,'checkpoint replay')
        require(to_snapshot(sim.state)==bundle['final_state'],'checkpoint final state')
        turns.append(bundle['turn']); covered.extend(bundle['request_ids'])
    reserved=[r['id'] for r in ledger.rows if r['match_id']==slot['match_id']]
    require(covered==reserved,'uncommitted request/turn after interruption: manual evidence resolution required; never resend')
    provider=None
    terminal=None
    if turns and turns[-1].get('provider_failure'):
        terminal='REQUEST_LIMIT' if turns[-1]['error_category']=='request_ceiling' else 'PROVIDER_FORFEIT'
    while not terminal and sim.state.winner_player_id is None and len(turns)<limits['player_turns'] and sim.state.turn<limits['full_rounds']:
        ledger.guard()
        part=ArenaSimulation(from_snapshot(to_snapshot(sim.state)))
        start_requests=len(ledger.rows); started=time.perf_counter()
        if part.state.active_player_id==slot['luna_side']:
            if provider is None:
                provider=provider_factory(slot,ledger)
                require(provider.configuration()==p['configuration'],'provider profile mismatch')
                require(provider.name=='openai' and provider.repair_version==p['repair'] and
                        provider.schema_version==p['schema'] and provider.repair is True and
                        provider.prompt_version==('arena-step-prompt-v3' if slot['arm']=='stepwise' else 'arena-turn-prompt-v6'),
                        'provider/control binding mismatch')
            provider.turn_ordinal=len(turns)+1
            row=CandidateController(provider,mode=slot['arm']).run_turn(part)
            if row['provider_failure']:
                error=row['error_category']
                if error=='request_ceiling': terminal='REQUEST_LIMIT'
                elif error in PROVIDER_FAILURES: terminal='PROVIDER_FORFEIT'
                else: raise IntegrityError(f'unclassified provider error: {error}')
            if slot['arm']=='stepwise' and row['execution_invalidities']:
                raise IntegrityError('current catalog execution defect')
        else:
            row=heuristic_turn(part)
        row['control_wall_seconds']=time.perf_counter()-started
        request_ids=[r['id'] for r in ledger.rows[start_requests:]]
        require(row['provider_requests']==len(request_ids),'request ledger mismatch')
        # Include failed transports in trace accounting, not just successful responses.
        if row.get('waves'):
            attempts=[a for w in row['waves'] for a in w['inference']['attempts']]
            require(len(attempts)==len(request_ids),'attempt count mismatch')
            for a,rid in zip(attempts,request_ids): a['ledger_id']=rid
        bundle=dict(ordinal=len(turns)+1,turn=row,trace=part.trace(),final_state=to_snapshot(part.state),request_ids=request_ids)
        bundle['request_files']={file.relative_to(root).as_posix():sha(file) for rid in request_ids
            for file in sorted((Path(root)/'requests'/f'{rid:06d}').glob('*.json'))}
        bundle['sha256']=digest(bundle)
        write_new(directory/'turns'/f'{len(turns)+1:04d}.json',bundle)
        for entry in part.trace()['entries']:
            require(sim.execute(command_from_dict(entry['command']))==entry,'online command replay mismatch')
        turns.append(row)
        if stop_after_turn and len(turns)==stop_after_turn:
            raise InterruptedError('injected interruption at durable turn checkpoint')
    engine_winner=sim.state.winner_player_id
    if engine_winner:
        terminal='CORE_DESTRUCTION' if any(c.hp==0 for c in sim.state.cores.values()) else 'TEAM_ELIMINATION'
    terminal=terminal or 'TURN_LIMIT'
    winner=slot['heuristic_side'] if terminal=='PROVIDER_FORFEIT' else engine_winner
    result=dict(match_id=slot['match_id'],slot=slot['id'],arm=slot['arm'],batch=slot['batch'],luna_side=slot['luna_side'],
        winner=winner,engine_winner=engine_winner,terminal_cause=terminal,
        luna_outcome='win' if winner==slot['luna_side'] else 'loss' if winner else 'limit',
        player_turns=len(turns),rounds_completed=sim.state.turn,rounds_started=(len(turns)+1)//2,
        requests=sum(r['provider_requests'] for r in turns),
        provider_failure_category=turns[-1]['error_category'] if terminal=='PROVIDER_FORFEIT' else None,
        limit_category=terminal if terminal in ('TURN_LIMIT','REQUEST_LIMIT') else None,
        active_control_seconds=sum(r['control_wall_seconds'] for r in turns),
        metrics=match_metrics(sim.trace(),turns,slot['luna_side']))
    match_ids=[r['id'] for r in ledger.rows if r['match_id']==slot['match_id']]
    external=dict(ids=match_ids,files={p.relative_to(root).as_posix():sha(p)
        for rid in match_ids for p in sorted((Path(root)/'requests'/f'{rid:06d}').glob('*.json'))})
    if (directory/'request-ledger.json').exists():
        require(read(directory/'request-ledger.json')==external,'request journal mismatch')
    else: write_new(directory/'request-ledger.json',external)
    for name,value in [('command-trace',sim.trace()),('final-state',to_snapshot(sim.state)),('result',result)]:
        target=directory/f'{name}.json'
        if target.exists(): require(read(target)==value,'partial finalization mismatch')
        else: write_new(target,value)
    checked=verify_match(directory,expected=slot,contract=contract)
    if not (directory/'replay-verification.json').exists(): write_new(directory/'replay-verification.json',checked)
    seal(directory)
    return result


def integrity(root,contract,*,replay_from=0):
    root=Path(root); completed=[]; request_ids=[]
    trusted={}
    if replay_from:
        require(replay_from%30==0,'trusted replay prefix must end at a batch gate')
        gate=read(root/'gates'/f'batch-{replay_from//30:02d}.json')
        require(gate['matches']==replay_from and gate['contract_sha256']==contract['sha256'] and gate['success'],
                'missing trusted replay gate')
        trusted=gate['match_seals']
    ledger=Ledger(root,contract['payload']['limits'])
    for slot in contract['payload']['schedule']:
        directory=root/'matches'/slot['match_id']
        if not (directory/'seal.json').exists(): break
        check_seal(directory)
        if slot['ordinal']>replay_from:
            checked=verify_match(directory,expected=slot,contract=contract)
        else:
            require(trusted.get(slot['match_id'])==sha(directory/'seal.json'),'previous replay seal changed')
            checked=read(directory/'replay-verification.json')
            require(checked['success'],'previous replay failed')
            external=read(directory/'request-ledger.json')
            require(external['ids']==checked['request_ids'],'previous request coverage changed')
            for relative,value in external['files'].items():
                require(sha(root/relative)==value,'previous request evidence changed')
        request_ids.extend(checked['request_ids'])
        completed.append(read(directory/'result.json'))
    sealed=list((root/'matches').glob('*/seal.json'))
    require(len(sealed)==len(completed),'completed matches not a schedule prefix')
    require(request_ids==list(range(1,len(request_ids)+1)),'duplicate/missing request coverage')
    for rid in request_ids:
        folder=root/'requests'/f'{rid:06d}'
        require((folder/'receipt.json').is_file() and (folder/'payload.json').is_file(),'missing request receipt')
        reservation=read(folder/'reservation.json')
        require(reservation==ledger.rows[rid-1],'ledger mutation')
    for path in sorted((root/'gates').glob('batch-*.json')):
        gate=read(path)
        require(gate['success'] and gate['contract_sha256']==contract['sha256'],'batch gate contract mismatch')
        require(gate['matches']==gate['batch']*30 and gate['matches']<=len(completed),'batch gate count mismatch')
        seals={r['match_id']:sha(root/'matches'/r['match_id']/'seal.json') for r in completed[:gate['matches']]}
        require(gate['match_seals']==seals,'batch gate seal mismatch')
        require(gate['requests']==sum(r['requests'] for r in completed[:gate['matches']]),'batch gate requests mismatch')
    limits=contract['payload']['limits']
    require(len(ledger.rows)<=limits['global_requests'],'global request overrun')
    for arm in ARMS:
        require(sum(r['arm']==arm for r in ledger.rows)<=limits['per_control'][arm],'control request overrun')
        for batch in range(1,11):
            require(sum(r['arm']==arm and r['batch']==batch for r in ledger.rows)<=limits['per_batch_control'][arm],
                    'batch/control request overrun')
    for batch in range(1,11):
        require(sum(r['batch']==batch for r in ledger.rows)<=limits['batch_requests'],'batch request overrun')
    return dict(success=True,completed_matches=len(completed),replay_verified=len(completed),
        completed_requests=len(request_ids),reserved_requests=len(ledger.rows),results=completed,
        pending_requests=len(ledger.rows)-len(request_ids))


def refresh_views(root,contract,checked):
    root=Path(root)
    derived(root/'match-index.json',dict(completed=[r['match_id'] for r in checked['results']],
        next_ordinal=len(checked['results'])+1))
    derived(root/'request-ledger.json',dict(reservations=Ledger(root).rows,
        completed_requests=checked['completed_requests'],pending_requests=checked['pending_requests']))
    derived(root/'integrity.json',{k:v for k,v in checked.items() if k!='results'})
    temp=root/'results.jsonl.tmp'
    temp.write_text(''.join(json.dumps(r)+'\n' for r in checked['results']),encoding='utf-8')
    os.replace(temp,root/'results.jsonl')


def run(root,contract,*,through_batch,mode='fake',provider_factory=None,guard=lambda:None,
        stop_after_matches=None,stop_after_turn=None):
    require(type(through_batch) is int and 1<=through_batch<=10,'explicit batch range 1..10 required')
    root=Path(root)
    with exclusive(root):
        guard()
        manifest=dict(benchmark=ID,contract_sha256=contract['sha256'],mode=mode,
            synthetic_telemetry=mode=='fake',live_inference_authorized=False if mode=='fake' else 'external explicit scope required')
        if (root/'benchmark-manifest.json').exists():
            require(read(root/'benchmark-manifest.json')==manifest,'run mode/contract mismatch')
        else:
            write_new(root/'benchmark-manifest.json',manifest)
            write_new(root/'contract.json',contract)
            write_new(root/'schedule.json',contract['payload']['schedule'])
        require(read(root/'contract.json')==contract and read(root/'schedule.json')==contract['payload']['schedule'],
                'run contract/schedule mutation')
        checked=integrity(root,contract)
        # A crash after the last match seal but before the gate may finish that gate offline.
        for batch in range(1,len(checked['results'])//30+1):
            path=root/'gates'/f'batch-{batch:02d}.json'
            if not path.exists():
                prefix=checked['results'][:batch*30]
                write_new(path,dict(batch=batch,success=True,matches=batch*30,
                    requests=sum(r['requests'] for r in prefix),source_verified=True,contract_sha256=contract['sha256'],
                    match_seals={r['match_id']:sha(root/'matches'/r['match_id']/'seal.json') for r in prefix}))
        require(len(checked['results'])<=through_batch*30,'authorization scope precedes completed prefix')
        ledger=Ledger(root,contract['payload']['limits'],guard)
        if provider_factory is None:
            require(mode=='fake','live provider factory required')
            provider_factory=lambda slot,book:JournalProvider(OpenAISettings(),slot=slot,ledger=book,fake=True)
        for slot in contract['payload']['schedule'][len(checked['results']):through_batch*30]:
            guard()
            run_match(root,slot,contract,ledger,provider_factory,stop_after_turn=stop_after_turn)
            completed=slot['ordinal']
            if completed % 30==0:
                guard(); checked=integrity(root,contract,replay_from=completed-30); refresh_views(root,contract,checked)
                gate=dict(batch=slot['batch'],success=True,matches=completed,requests=checked['completed_requests'],
                    source_verified=True,contract_sha256=contract['sha256'],
                    match_seals={s['match_id']:sha(root/'matches'/s['match_id']/'seal.json')
                                 for s in contract['payload']['schedule'][:completed]})
                write_new(root/'gates'/f'batch-{slot["batch"]:02d}.json',gate)
                print(json.dumps(dict(batch=slot['batch'],matches=completed,requests=checked['completed_requests'],integrity='passed')),flush=True)
            if stop_after_matches and completed==stop_after_matches: break
        guard()
        sealed_count=len(list((root/'matches').glob('*/seal.json')))
        checked=integrity(root,contract,replay_from=sealed_count//30*30)
        refresh_views(root,contract,checked)
        return checked


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('freeze','verify','dry-run','run-live','analyze'))
    parser.add_argument('--contract',type=Path,default=DEFAULT_CONTRACT)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--through-batch',type=int)
    parser.add_argument('--authorize-live',choices=(ID,))
    parser.add_argument('--stop-after-matches',type=int)
    args=parser.parse_args(argv)
    if args.command=='freeze':
        print(freeze(args.contract)['sha256']); return 0
    contract=verify(args.contract)
    if args.command=='verify' and args.output is None:
        print(json.dumps(dict(contract=contract['sha256'],success=True))); return 0
    require(args.output is not None,'--output required')
    if args.command=='verify':
        with exclusive(args.output):
            checked=integrity(args.output,contract);refresh_views(args.output,contract,checked)
        print(json.dumps({k:v for k,v in checked.items() if k!='results'}));return 0
    if args.command=='analyze':
        from aig.arena.case_study_analysis import analyze
        with exclusive(args.output):
            checked=integrity(args.output,contract)
            analyze(args.output,checked['results'],contract)
        return 0
    require(args.through_batch is not None,'--through-batch required; no implicit multi-batch authorization')
    if args.command=='run-live':
        require(args.authorize_live==ID,'explicit live authorization acknowledgement required')
        settings=load_settings().openai
        require(settings.api_key is not None,'missing credentials; no preflight inference')
        require(settings.timeout_seconds==contract['payload']['limits']['provider_timeout_seconds'],'timeout drift')
        def factory(slot,ledger):
            return JournalProvider(settings,slot=slot,ledger=ledger)
        run(args.output,contract,through_batch=args.through_batch,mode='live',provider_factory=factory,
            guard=lambda:verify(args.contract))
    else:
        with no_network():
            run(args.output,contract,through_batch=args.through_batch,guard=lambda:verify(args.contract),
                stop_after_matches=args.stop_after_matches)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
