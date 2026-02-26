/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
export function makeArray<T>(object: T | T[]): T[] {
	return Array.isArray(object) ? object : [object];
}

export enum SpecLocationSource {
	GLOBAL = 'global',
	LOCAL = 'local',
}