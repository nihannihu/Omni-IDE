/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
// eslint-disable-next-line local/code-no-standalone-editor
import * as monaco from './out/vs/editor/editor.main.js';

monaco.editor.create(document.getElementById('container'), {
	value: 'Hello world'
});