import 'pinia'

declare module 'pinia' {
  export interface PiniaCustomProperties {
    /**
     * Properties added by pinia-plugin-persistedstate
     */
    $persistedState: {
      /**
       * A Promise that resolves when the store is hydrated.
       */
      isReady: () => Promise<void>;
      // You can add other properties exposed by the plugin if needed
    }
  }
}