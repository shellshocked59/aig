import '../css/main.css';
import '../css/arena.css';
import { createGameApi } from './api/game.js';
import { createArenaApi } from './api/arena.js';
import { mountEnvironments } from './environments.js';

mountEnvironments(document.querySelector('#app'), createGameApi(), createArenaApi());
