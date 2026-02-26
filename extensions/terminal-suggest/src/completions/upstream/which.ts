/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const programGenerator: Fig.Generator = {
	script: [
		"bash",
		"-c",
		`for i in $(echo $PATH | tr ":" "\n"); do find $i -maxdepth 1 -perm -111 -type f; done`,
	],
	postProcess: (out) =>
		out
			.split("\n")
			.map((path) => path.split("/")[path.split("/").length - 1])
			.map((pr) => ({ name: pr, description: "Executable file", type: "arg" })),
};

const completionSpec: Fig.Spec = {
	name: "which",
	description: "Locate a program in the user's PATH",
	args: {
		name: "names",
		isVariadic: true,
		generators: programGenerator,
		filterStrategy: "fuzzy",
		suggestCurrentToken: true,
	},
	options: [
		{
			name: "-s",
			description:
				"No output, return 0 if all the executables are found, 1 if not",
		},
		{
			name: "-a",
			description:
				"List all instances of executables found, instead of just the first",
		},
	],
};

export default completionSpec;