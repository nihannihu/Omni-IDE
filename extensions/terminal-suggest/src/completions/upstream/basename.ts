/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const completionSpec: Fig.Spec = {
	name: "basename",
	description: "Return filename portion of pathname",
	options: [
		{
			name: "-a",
			description: "Treat every argument as a string",
		},
		{
			name: "-s",
			description: "Suffix to remove from string",
			args: {
				name: "suffix",
			},
		},
	],
	args: {
		name: "string",
		description: "String to operate on (typically filenames)",
		isVariadic: true,
		template: "filepaths",
	},
};
export default completionSpec;