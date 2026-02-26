/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
let _fetch: typeof fetch;
try {
	_fetch = require('electron').net.fetch;
} catch {
	_fetch = fetch;
}
export default _fetch;