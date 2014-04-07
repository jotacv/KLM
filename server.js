
var keyboard = require('msi-keyboard');
var readline = require('readline');

// keyboard.color('left',{color: random.randomChoice(colors), intensity: 'high'});
// keyboard.color('middle',{color: random.randomChoice(colors), intensity: 'high'});
// keyboard.color('right',{color: random.randomChoice(colors), intensity: 'high'});

var rl = readline.createInterface({
	input: process.stdin,
	output: process.stdout,
	terminal: false
});

rl.on('line', function (cmd) {
	cmds=cmd.split(' ; ');
	console.log(cmd)
	if (cmds.length == 3){
		keyboard.color('left',{color: cmds[0], intensity: 'high'});
		keyboard.color('middle',{color: cmds[1], intensity: 'high'});
		keyboard.color('right',{color: cmds[2], intensity: 'high'});
	}
});