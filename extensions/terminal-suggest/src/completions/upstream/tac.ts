/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const completionSpec: Fig.Spec = {
	name: "tac",
	description: "Concatenate and print files in reverse",
	parserDirectives: {
		optionsMustPrecedeArguments: true,
	},
	options: [
		{
			name: "--help",
			description: "Display this help and exit",
		},
		{
			name: ["--before", "-b"],
			description: "Attach the separator before instead of after",
		},
		{
			name: ["--regex", "-r"],
			description: "Interpret the separator as a regular expression",
		},
		{
			name: ["--separator", "-s"],
			description: "Use STRING as the separator instead of newline",
			args: {
				name: "STRING",
			},
		},
		{
			name: "--version",
			description: "Output version information and exit",
		},
	],
	args: {
		name: "FILE",
		template: "filepaths",
	},
};
export default completionSpec;