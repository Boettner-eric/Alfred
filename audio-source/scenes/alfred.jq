{
  items: [.[] | {
      uid: .title,
      title: .title,
      icon: {path: .icon},
      subtitle: ("Input: " + .input + " | Output: " + .output),
      arg: ("input: " + .input + " | output: " + .output),
      mods: {
        ctrl: {
          valid: true,
          arg: .title,
          subtitle: ("copy \"" + .title + "\" to clipboard"),
        },
        shift: {
          valid: true,
          arg: ("input," + .input),
          subtitle: ("set input to " + .input),
        },
        alt: {
          valid: true,
          arg: ("output," + .output),
          subtitle: ("set output to " + .output),
        },
        cmd: {
          valid: true,
          arg: ("both," + .input + "," + .output),
          subtitle: ("set both input and output"),
        },
      },
    }
  ]
}
