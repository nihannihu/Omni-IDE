/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
export interface ICommentsConfiguration {
	openView: 'never' | 'file' | 'firstFile' | 'firstFileUnresolved';
	useRelativeTime: boolean;
	visible: boolean;
	maxHeight: boolean;
	collapseOnResolve: boolean;
}

export const COMMENTS_SECTION = 'comments';