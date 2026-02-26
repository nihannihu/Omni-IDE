/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { ILogger } from '../logging';

export const nulLogger = new class implements ILogger {
	trace(): void {
		// noop
	}
};