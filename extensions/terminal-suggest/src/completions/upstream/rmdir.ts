/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const completionSpec: Fig.Spec = {
	name: "rmdir",
	description: "Remove directories",
	args: {
		isVariadic: true,
		template: "folders",
	},

	options: [
		{
			name: "-p",
			description: "Remove each directory of path",
			isDangerous: true,
		},
	],
};

export default completionSpec;