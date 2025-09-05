{
  items: [.[] | {
      uid: .title,
      title: .title,
      icon: {path: .icon},
      subtitle: ("Input: " + .input + " | Output: " + .output),
      arg: ("input: " + .input + " | output: " + .output),
      mods: {
         cmd: {
          valid: true,
          arg: ("output," + .output),
          subtitle: ("set output to " + .output),
        },
         alt: {
          valid: true,
          arg: ("input," + .input),
          subtitle: ("set input to " + .input),
        },
        ctrl: {
          valid: true,
          arg: .title,
          subtitle: ("edit \"" + .title + "\" (todo)"),
        },
        # shift: {
        #   valid: true,
        #   arg: ("both," + .input + "," + .output),
        #   subtitle: ("set both input and output"),
        # },
      },
    }
  ]
}
