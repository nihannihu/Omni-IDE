/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const environmentVariableGenerator: Fig.Generator = {
	custom: async (tokens, _, context) => {
		if (tokens.length < 3 || tokens[tokens.length - 1].startsWith("$")) {
			return Object.keys(context.environmentVariables).map((suggestion) => ({
				name: `$${suggestion}`,
				type: "arg",
				description: "Environment Variable",
			}));
		} else {
			return [];
		}
	},
	trigger: "$",
};

const completionSpec: Fig.Spec = {
	name: "echo",
	description: "Write arguments to the standard output",
	args: {
		name: "string",
		isVariadic: true,
		optionsCanBreakVariadicArg: false,
		suggestCurrentToken: true,
		generators: environmentVariableGenerator,
	},
	options: [
		{
			name: "-n",
			description: "Do not print the trailing newline character",
		},
		{
			name: "-e",
			description: "Interpret escape sequences",
		},
		{
			name: "-E",
			description: "Disable escape sequences",
		},
	],
};

export default completionSpec;