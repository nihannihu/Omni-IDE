/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { EditorContributionInstantiation, registerEditorContribution } from '../../../browser/editorExtensions.js';
import { MiddleScrollController } from './middleScrollController.js';

registerEditorContribution(MiddleScrollController.ID, MiddleScrollController, EditorContributionInstantiation.BeforeFirstInteraction);