import { ref, computed } from 'vue';
import type { Router, RouteLocationNormalized } from 'vue-router';

const HISTORY_STORAGE_KEY = 'navigationHistory';

// Load history from sessionStorage or initialize as an empty array
const initialHistory: string[] = JSON.parse(sessionStorage.getItem(HISTORY_STORAGE_KEY) || '[]');
const history = ref<string[]>(initialHistory);

// Function to save history to sessionStorage
function saveHistory() {
  sessionStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history.value));
}

/**
 * A reactive property that indicates if there's a previous page to go back to.
 */
export const canGoBack = computed(() => history.value.length > 1);

/**
 * The current route path from our history stack.
 */
export const currentRoutePath = computed(() => {
  if (history.value.length === 0) {
    return null;
  }
  return history.value[history.value.length - 1];
});

/**
 * Navigates to the previous route in the history stack.
 * It uses router.replace() to avoid adding the "back" navigation itself to the history.
 * @param router The Vue Router instance.
 */
export function goBack(router: Router) {
  if (canGoBack.value) {
    // We simply trigger the browser's back mechanism.
    // The history listener will handle the state update.
    router.back();
  }
}

/**
 * Installs the navigation history tracker.
 * This function should be called once when the application initializes.
 * @param router The Vue Router instance.
 */
export function installNavigationHistory(router: Router) {
  router.afterEach((to, from, failure) => {
    if (failure) {
      // Do not track failed navigations
      return;
    }

    const toFullPath = to.fullPath;
    const historyLength = history.value.length;
    const lastPathInHistory = historyLength > 0 ? history.value[historyLength - 1] : null;

    // A navigation is considered 'back' if the destination is the second-to-last item in our stack.
    // This is a robust way to detect if the user clicked the browser's back button or our custom one.
    const isBackNavigation = historyLength > 1 && history.value[historyLength - 2] === toFullPath;

    if (isBackNavigation) {
      // If it's a 'back' navigation, we just pop the last state from our history.
      history.value.pop();
    } else {
      // For any 'forward' or 'push' navigation, we add the new route to the history.
      // This prevents incorrect truncation when navigating to an already visited page via a menu click.
      // We avoid pushing the same path consecutively, which can happen with redirects.
      if (toFullPath !== lastPathInHistory) {
        history.value.push(toFullPath);
      }
    }

    saveHistory();
  });

  // Initial population of history
  if (history.value.length === 0 && router.currentRoute.value.fullPath !== '/') {
      history.value.push(router.currentRoute.value.fullPath);
      saveHistory();
  }
}