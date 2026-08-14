import { initFavorites } from "./favorites.js";
import { initGenerator } from "./generator.js";
import { initBrowserHistory } from "./history.js";
import { initResultReveal, initScrollReveals } from "./motion.js";
import { initTabs, initTrends } from "./navigation.js";
import { initStreaming } from "./streaming.js";

document.documentElement.classList.add("motion-ready");

initGenerator();
initTabs();
initTrends();
initBrowserHistory();
initStreaming();
initResultReveal();
initFavorites();
initScrollReveals();
