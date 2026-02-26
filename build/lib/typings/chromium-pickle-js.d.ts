/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
declare module 'chromium-pickle-js' {
	export interface Pickle {
		writeString(value: string): void;
		writeUInt32(value: number): void;

		toBuffer(): Buffer;
	}

	export function createEmpty(): Pickle;
}