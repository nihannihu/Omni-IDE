/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
declare module 'vscode' {

	// https://github.com/microsoft/vscode/issues/106744

	export interface NotebookCellOutput {
		/**
		 * @deprecated
		 */
		id: string;
	}
}