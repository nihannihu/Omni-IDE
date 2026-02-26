/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const completionSpec: Fig.Spec = {
	name: "tee",
	description: "Duplicate standard input",
	options: [
		{
			name: "-a",
			description:
				"Append the output to the files rather than overwriting them",
		},
		{
			name: "-i",
			description: "Ignore the SIGINT signal",
		},
	],
	args: {
		name: "file",
		description: "Pathname of an output file",
		isVariadic: true,
		template: "filepaths",
	},
};
export default completionSpec;