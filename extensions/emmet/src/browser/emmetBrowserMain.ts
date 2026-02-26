/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import * as vscode from 'vscode';
import { activateEmmetExtension } from '../emmetCommon';

export function activate(context: vscode.ExtensionContext) {
	activateEmmetExtension(context);
}