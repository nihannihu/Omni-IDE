/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { bootstrapWebWorker } from '../../../base/common/worker/webWorkerBootstrap.js';
import { EditorWorker } from './editorWebWorker.js';

bootstrapWebWorker(() => new EditorWorker(null));