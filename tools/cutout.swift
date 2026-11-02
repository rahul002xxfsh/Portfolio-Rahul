// Lifts the subject out of a photo with Apple Vision. Usage: swift cutout.swift in.jpg out.png
import Foundation
import Vision
import CoreImage
let a = CommandLine.arguments
let input = CIImage(contentsOf: URL(fileURLWithPath: a[1]))!
let req = VNGenerateForegroundInstanceMaskRequest()
let h = VNImageRequestHandler(ciImage: input)
try h.perform([req])
guard let r = req.results?.first else { print("no subject"); exit(1) }
let mask = try r.generateScaledMaskForImage(forInstances: r.allInstances, from: h)
let m = CIImage(cvPixelBuffer: mask)
let f = CIFilter(name: "CIBlendWithMask", parameters: [kCIInputImageKey: input, kCIInputMaskImageKey: m, kCIInputBackgroundImageKey: CIImage.empty()])!
let ctx = CIContext()
try ctx.writePNGRepresentation(of: f.outputImage!, to: URL(fileURLWithPath: a[2]), format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
print("ok")
