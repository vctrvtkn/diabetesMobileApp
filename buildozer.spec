[app]
title = Калькулятор ХЕ
package.name = xecalculator
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

icon.filename = %(source.dir)s/icon.png

version = 0.1.2
requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

android.archs = arm64-v8a
android.api = 35
android.minapi = 28


[buildozer]
log_level = 2
warn_on_root = 1
