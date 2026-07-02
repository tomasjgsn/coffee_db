import { defineConfig } from '@playwright/test';
import { join } from 'node:path';

const e2eDir = join(import.meta.dirname, '.e2e-data');

export default defineConfig({
	testDir: 'tests/e2e',
	webServer: {
		command: 'npm run e2e:prepare && npm run build && npm run preview',
		port: 4173,
		reuseExistingServer: false,
		env: {
			COFFEE_DB_PATH: join(e2eDir, 'coffee.db'),
			COFFEE_DATA_DIR: e2eDir
		}
	},
	use: {
		baseURL: 'http://localhost:4173'
	}
});
