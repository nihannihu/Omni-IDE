/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const completionSpec: Fig.Spec = {
	name: "source",
	description: "Source files in shell",
	args: {
		isVariadic: true,
		name: "File to source",
		template: "filepaths",
	},
};

export default completionSpec;