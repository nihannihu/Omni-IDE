/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
/**
 * When `true`, self-hosting uses esbuild for fast transpilation (build/next)
 * and gulp-tsb only for type-checking (`noEmit`).
 *
 * When `false`, gulp-tsb does both transpilation and type-checking (old behavior).
 */
export const useEsbuildTranspile = true;