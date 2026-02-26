/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const completionSpec: Fig.Spec = {
	name: "tail",
	description: "Display the last part of a file",
	args: {
		isVariadic: true,
		template: "filepaths",
	},
	options: [
		{
			name: "-f",
			description: "Wait for additional data to be appended",
		},
		{
			name: "-r",
			description: "Display in reverse order",
		},
	],
};

export default completionSpec;