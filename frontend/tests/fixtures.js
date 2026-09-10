// Small public-contract fixture. Values deliberately differ from engine defaults
// so rendering tests detect hard-coded costs and movement allowances.
export function gameFixture() {
  return {
    game: { turn: 3, activePlayerId: 'A', status: 'started' },
    players: ['A', 'B'].map((id) => ({
      id, controller: 'human', eliminated: false, gold: 12, scienceStored: 7,
      researchTarget: 'archery', researchedTechnologies: ['agriculture'],
      availableResearch: [{ technology: 'archery', cost: 37 }, { technology: 'bronze_working', cost: 42 }],
      researchCost: 37, researchRemaining: 30,
    })),
    map: { width: 3, height: 2, origin: { x: 0, y: 0 },
      tiles: ['grassland', 'plains', 'forest', 'hills', 'mountains', 'water'].map((terrain, index) => ({
        x: index % 3, y: Math.floor(index / 3), terrain, ownerId: index === 0 ? 'A' : null,
      })),
    },
    units: [
      { id: 'unit-1', ownerId: 'A', type: 'settler', x: 0, y: 0, hp: 100, movesRemaining: 2, maxMovement: 7, attackRange: 0 },
      { id: 'unit-2', ownerId: 'A', type: 'warrior', x: 0, y: 0, hp: 70, movesRemaining: 1, maxMovement: 3, attackRange: 1 },
      { id: 'unit-3', ownerId: 'B', type: 'scout', x: 1, y: 0, hp: 80, movesRemaining: 2, maxMovement: 2, attackRange: 1 },
      { id: 'unit-4', ownerId: 'B', type: 'spearman', x: 1, y: 0, hp: 60, movesRemaining: 1, maxMovement: 1, attackRange: 1 },
    ],
    cities: [{
      id: 'city-1', ownerId: 'A', name: 'New Hope', x: 0, y: 0,
      population: 2, foodStored: 9, productionStored: 11, productionTarget: 'warrior',
      availableProduction: [{ unitType: 'warrior', cost: 53 }, { unitType: 'scout', cost: 47 }],
      productionCost: 53, productionRemaining: 42,
    }],
  };
}
