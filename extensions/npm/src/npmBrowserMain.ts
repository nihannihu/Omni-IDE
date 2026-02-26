/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import * as httpRequest from 'request-light';
import * as vscode from 'vscode';
import { addJSONProviders } from './features/jsonContributions';

export async function activate(context: vscode.ExtensionContext): Promise<void> {
	context.subscriptions.push(addJSONProviders(httpRequest.xhr, undefined));
}

export function deactivate(): void {
}