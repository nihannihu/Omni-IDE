/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import * as vscode from 'vscode';

/**
 * Minimal version of {@link vscode.TextDocument}.
 */
export interface ITextDocument {
	readonly uri: vscode.Uri;
	readonly version: number;

	getText(range?: vscode.Range): string;

	positionAt(offset: number): vscode.Position;
}
