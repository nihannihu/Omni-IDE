/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
declare module '@vscode/gulp-electron' {

	interface MainFunction {
		(options: any): NodeJS.ReadWriteStream;
		dest(destination: string, options: any): NodeJS.ReadWriteStream;
	}

	const main: MainFunction;
	export default main;
}