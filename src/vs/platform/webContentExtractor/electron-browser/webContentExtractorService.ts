/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { registerMainProcessRemoteService, registerSharedProcessRemoteService } from '../../ipc/electron-browser/services.js';
import { ISharedWebContentExtractorService, IWebContentExtractorService } from '../common/webContentExtractor.js';

registerMainProcessRemoteService(IWebContentExtractorService, 'webContentExtractor');
registerSharedProcessRemoteService(ISharedWebContentExtractorService, 'sharedWebContentExtractor');