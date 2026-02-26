/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { WorkbenchPhase, registerWorkbenchContribution2 } from '../../../common/contributions.js';
import { SyncScroll as ScrollLocking } from './scrollLocking.js';

registerWorkbenchContribution2(
	ScrollLocking.ID,
	ScrollLocking,
	WorkbenchPhase.Eventually // registration only
);