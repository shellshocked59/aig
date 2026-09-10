import '../css/main.css';
import { createGameApi } from './api/game.js';
import { mountGame } from './game.js';

mountGame(document.querySelector('#app'), createGameApi());
