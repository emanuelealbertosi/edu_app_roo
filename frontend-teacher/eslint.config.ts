import globals from 'globals'
import pluginJs from '@eslint/js'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import eslintConfigPrettier from 'eslint-config-prettier'


export default [
  { files: ['**/*.{js,mjs,cjs,ts,vue}'] },
  { languageOptions: { globals: globals.browser } },
  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/essential'], // Use flat config for Vue
  eslintConfigPrettier, // Make sure this is last
  {
    rules: {
      // Override/add rules here if needed
      'vue/multi-word-component-names': 'off', // Example: disable rule for simple component names
    }
  }
]