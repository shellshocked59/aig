"""Phase 10B offline reconstruction; metadata must already exist. No network."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import argparse, hashlib, importlib.util, json, time
from functools import lru_cache

BASE = Path('.local/arena-phase10b-ollama-context-investigation-20260913')
sys.path.insert(0, str(BASE/'offline-packages'))

def guard(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'):
        raise RuntimeError('Phase 10B analysis is offline only')
sys.addaudithook(guard)

import regex
from jinja2 import Environment
from aig.arena.constrained_study import captured_request
from aig.arena.ai.observation import ArenaObservation, build_observation, OBSERVATION_V2
from aig.arena.benchmark_versions import frozen_probe
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import canonical_json

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE/'derived')
    out = parser.parse_args().output
    out.mkdir(exist_ok=False)
    def write(name, data):
        (out/name).write_text(json.dumps(data, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')
    show = read(BASE/'show.json')
    info = show['model_info']
    vocab = info['tokenizer.ggml.tokens']
    ids = {v:i for i,v in enumerate(vocab)}
    merges = {tuple(v.split(' ')): i for i,v in enumerate(info['tokenizer.ggml.merges'])}
    byte_values = list(range(33,127))+list(range(161,173))+list(range(174,256))
    byte_chars = byte_values[:]
    n = 0
    for b in range(256):
        if b not in byte_values:
            byte_values.append(b); byte_chars.append(256+n); n += 1
    enc = dict(zip(byte_values,map(chr,byte_chars)))
    dec = {v:k for k,v in enc.items()}
    pattern = regex.compile(r"(?:'[sS]|'[tT]|'[rR][eE]|'[vV][eE]|'[mM]|'[lL][lL]|'[dD])|[^\r\n\p{L}\p{N}]?[\p{L}\p{M}]+|\p{N}| ?[^\s\p{L}\p{M}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+")
    specials = {v for v,t in zip(vocab,info['tokenizer.ggml.token_type']) if t in (3,4)}
    special_pattern = regex.compile('('+ '|'.join(regex.escape(v) for v in sorted(specials,key=len,reverse=True))+')')
    @lru_cache(maxsize=20000)
    def bpe(word):
        parts = [enc[b] for b in word.encode('utf-8')]
        while len(parts)>1:
            rank, idx = min((merges.get((a,b),float('inf')),i) for i,(a,b) in enumerate(zip(parts,parts[1:])))
            if rank == float('inf'): break
            parts[idx:idx+2] = [parts[idx]+parts[idx+1]]
        return tuple(ids[v] for v in parts)
    def tokenize(text):
        result = []
        for chunk in special_pattern.split(text):
            if chunk in specials: result.append(ids[chunk]); continue
            pieces = pattern.findall(chunk)
            assert ''.join(pieces)==chunk
            for word in pieces: result.extend(bpe(word))
        # Verify lossless reconstruction independently of the merge loop.
        recovered = bytearray()
        for token in result:
            value = vocab[token]
            recovered.extend(value.encode() if value in specials else bytes(dec[c] for c in value))
        assert recovered.decode()==text
        return result
    template = Environment().from_string(show['template'])
    def render(req):
        return template.render(messages=req['messages'],tools=[],add_generation_prompt=True,enable_thinking=False)
    def metrics(req):
        text = render(req); tokens = tokenize(text)
        return dict(request_bytes=len(canonical_json(req).encode()),schema_bytes=len(canonical_json(req['format']).encode()),
            message_content_bytes=sum(len(m['content'].encode()) for m in req['messages']),
            rendered_prompt_bytes=len(text.encode()), reconstructed_tokens=len(tokens),
            headroom_after_256=4096-256-len(tokens),prompt_sha256=hashlib.sha256(text.encode()).hexdigest())
    study = read('.local/arena-phase10a-offline/results-final/study.json')
    mid = next(m for m in study['measurements'] if m['label']=='historical-midgame')
    midrow = read(mid['source'])['steps'][mid['step_index']]
    observations = {
        'simple-probe':build_observation(frozen_probe('snipe_vs_basic'),version=OBSERVATION_V2),
        'revive':build_observation(frozen_probe('revive_decision'),version=OBSERVATION_V2),
        'opening':build_observation(ArenaSimulation().state,version=OBSERVATION_V2),
        'historical-midgame':ArenaObservation.from_dict(midrow['observation'])}
    spec = importlib.util.spec_from_file_location('pinned_converter',BASE/'source-cpp-examples__json_schema_to_grammar.py')
    converter = importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
    measurements=[]
    for label,obs in observations.items():
        generic=captured_request(obs,'ollama',False);req=captured_request(obs,'ollama',True)
        assert req['messages']==generic['messages']
        assert render(req)==render(generic)
        row=dict(label=label,observation_hash=obs.hash,observation_bytes=len(obs.canonical.encode()),**metrics(req))
        previous=next(m for m in study['measurements'] if m['label']==label)
        assert row['request_bytes']==previous['providers']['ollama']['constrained']['request_bytes']
        assert row['schema_bytes']==previous['providers']['ollama']['constrained']['schema_bytes']
        write(label+'-request.json',req)
        (out/(label+'-prompt.txt')).write_text(render(req),encoding='utf-8')
        write(label+'-token-ids.json',tokenize(render(req)))
        start=time.perf_counter()
        c=converter.SchemaConverter(prop_order={},allow_fetch=False,dotall=False,raw_pattern=False)
        c.visit(req['format'],''); grammar=c.format_grammar()
        row.update(python_converter_seconds=time.perf_counter()-start,standalone_grammar_bytes=len(grammar.encode()),
                   standalone_grammar_rules=len(grammar.splitlines()),legal_action_branches=len(obs.to_dict()['legal_actions']))
        (out/(label+'-standalone.gbnf')).write_text(grammar,encoding='utf-8')
        measurements.append(row)
    history=Path('.local/arena-phase9d-action-id-forensics-20260913/derived-01')
    telemetry=[]
    for row in read(history/'revive-decisions.json'):
        req=read(history/row['request_file'])
        m=metrics(req)
        recorded=row['telemetry'][0]['metrics']
        telemetry.append(dict(mode=row['mode'],trial=row['trial'],step=row['step'],state_hash=row['state_hash'],
            **m,recorded_prompt_eval_count=recorded.get('prompt_eval_count'),recorded_eval_count=recorded.get('eval_count'),
            token_delta=m['reconstructed_tokens']-recorded.get('prompt_eval_count',0),source=str(history/row['request_file'])))
    write('measurements.json',measurements);write('revive-telemetry.json',telemetry)
    assert len(telemetry)==36 and all(r['token_delta']==0 for r in telemetry)
    assert next(r for r in measurements if r['label']=='historical-midgame')['reconstructed_tokens']==midrow['attempts'][0]['metrics']['prompt_eval_count']
    write('method.json',dict(model=show['details'],metadata_sha256=hashlib.sha256((BASE/'show.json').read_bytes()).hexdigest(),
        tokenizer='GGUF vocabulary + ranked GPT2 byte BPE + pinned llama.cpp qwen35 regex; special types 3/4; no BOS',
        template='Jinja2 rendering of metadata template; text messages, no tools, think=false',
        caveat='Offline replica, not server tokenizer or native C++ grammar execution',
        lossless_roundtrips=True,live_requests=0,network_calls=0))
    print(json.dumps(dict(measurements=measurements,historical_comparisons=len(telemetry),
                         exact_token_matches=sum(r['token_delta']==0 for r in telemetry)),indent=2))

if __name__=='__main__':main()
