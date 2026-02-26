/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
/**
 * @typedef {{
 *   id: number,
 *   fn: !Function,
 *   context: (!Object|undefined)
 * }}
 * @private
 */
goog.dom.animationFrame.Task_;


/**
 * @typedef {{
 *   measureTask: goog.dom.animationFrame.Task_,
 *   mutateTask: goog.dom.animationFrame.Task_,
 *   state: (!Object|undefined),
 *   args: (!Array|undefined),
 *   isScheduled: boolean
 * }}
 * @private
 */
goog.dom.animationFrame.TaskSet_;