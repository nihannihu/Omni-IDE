/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
declare module 'vscode' {
	export namespace authentication {
		/**
		 * @deprecated Use {@link getSession()} {@link AuthenticationGetSessionOptions.silent} instead.
		 */
		export function hasSession(providerId: string, scopes: readonly string[]): Thenable<boolean>;
	}
}