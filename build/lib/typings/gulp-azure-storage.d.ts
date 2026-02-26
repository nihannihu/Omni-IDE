/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
declare module 'gulp-azure-storage' {
	import { ThroughStream } from 'event-stream';

	export function upload(options: any): ThroughStream;
}