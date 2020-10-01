# -*- coding: utf-8 -*-

import af

job = af.Job('Blender Test')

block = af.Block('render', 'blender')
block.setCommand('blender -b scene.blend -s @#@ -e @#@ -a')
block.setNumeric(1, 20, 2)

job.blocks.append(block)

print('')
job.output()
print('')

job.send()
