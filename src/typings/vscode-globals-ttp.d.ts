/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
// AMD2ESM migration relevant

declare global {

	var _VSCODE_WEB_PACKAGE_TTP: Pick<TrustedTypePolicy, 'name' | 'createScriptURL'> | undefined;
}

// fake export to make global work
export { };