/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
'use strict';
var M;
(function (M) {
    var C = (function () {
        function C() {
        }
        return C;
    })();
    (function (x, property, number) {
        if (property === undefined) { property = w; }
        var local = 1;
        // unresolved symbol because x is local
        //self.x++;
        self.w--; // ok because w is a property
        property;
        f = function (y) {
            return y + x + local + w + self.w;
        };
        function sum(z) {
            return z + f(z) + w + self.w;
        }
    });
})(M || (M = {}));
var c = new M.C(12, 5);