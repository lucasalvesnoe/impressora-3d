// Câmera de um iPhone ligado por cabo, lida pela tela do aparelho (app Câmera aberto e apontado para a impressora).
// O macOS expõe a tela do iPhone como dispositivo "muxed" do CoreMediaIO depois de liberar os dispositivos de
// captura de tela; daí basta ler os quadros e gravar o mais recente em JPEG, cortando as barras do app Câmera.
//
// Uso:
//   iphone_cabo --lista                  lista os iPhones vistos pelo cabo e sai (0 = achou, 2 = nenhum)
//   iphone_cabo saida.jpg [topo base [giro]]  grava um quadro por segundo; topo/base = fração da altura mantida
//                                        (padrão 0.0705 0.821: tira a barra do flash e os botões do app Câmera);
//                                        giro = 0, 90 ou -90 graus (anti-horário) para o iPhone deitado
// Compilar: swiftc -O -o scripts/iphone_cabo scripts/iphone_cabo.swift
import AVFoundation
import CoreMediaIO
import CoreImage

var prop = CMIOObjectPropertyAddress(
    mSelector: CMIOObjectPropertySelector(kCMIOHardwarePropertyAllowScreenCaptureDevices),
    mScope: CMIOObjectPropertyScope(kCMIOObjectPropertyScopeGlobal),
    mElement: CMIOObjectPropertyElement(kCMIOObjectPropertyElementMain))
var permitir: UInt32 = 1
CMIOObjectSetPropertyData(CMIOObjectID(kCMIOObjectSystemObject), &prop, 0, nil,
                          UInt32(MemoryLayout<UInt32>.size), &permitir)

let args = CommandLine.arguments
let soLista = args.count > 1 && args[1] == "--lista"

func iphones() -> [AVCaptureDevice] {
    AVCaptureDevice.DiscoverySession(deviceTypes: [.external], mediaType: .muxed, position: .unspecified)
        .devices.filter { $0.modelID.contains("iOS") || $0.localizedName.lowercased().contains("iphone") }
}

// o dispositivo leva alguns segundos para aparecer depois da liberação
var achados: [AVCaptureDevice] = []
for _ in 0..<(soLista ? 8 : 40) {
    achados = iphones()
    if !achados.isEmpty { break }
    RunLoop.current.run(until: Date().addingTimeInterval(0.5))
}
if soLista {
    for d in achados { print(d.localizedName) }
    exit(achados.isEmpty ? 2 : 0)
}
guard let disp = achados.first else { FileHandle.standardError.write("nenhum iPhone pelo cabo\n".data(using: .utf8)!); exit(2) }

let saida = args.count > 1 ? args[1] : "iphone_cabo.jpg"
let topo = args.count > 3 ? Double(args[2]) ?? 0.0705 : 0.0705
let base = args.count > 3 ? Double(args[3]) ?? 0.821 : 0.821
let giro = args.count > 4 ? Double(args[4]) ?? 0 : 0
print("usando:", disp.localizedName); fflush(stdout)

final class Gravador: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    let ctx = CIContext(); var ultimo = Date.distantPast
    func captureOutput(_ o: AVCaptureOutput, didOutput sb: CMSampleBuffer, from c: AVCaptureConnection) {
        guard Date().timeIntervalSince(ultimo) >= 1, let pb = CMSampleBufferGetImageBuffer(sb) else { return }
        ultimo = Date()
        let img = CIImage(cvPixelBuffer: pb)
        let h = img.extent.height
        // CoreImage tem origem embaixo: o corte vai de (1 - base) a (1 - topo) da altura
        let corte = CGRect(x: 0, y: h * (1 - base), width: img.extent.width, height: h * (base - topo))
        var final = img.cropped(to: corte).transformed(by: CGAffineTransform(translationX: 0, y: -h * (1 - base)))
        if giro != 0 {
            final = final.transformed(by: CGAffineTransform(rotationAngle: giro * .pi / 180))
            final = final.transformed(by: CGAffineTransform(translationX: -final.extent.minX, y: -final.extent.minY))
        }
        guard let cs = CGColorSpace(name: CGColorSpace.sRGB),
              let jpg = ctx.jpegRepresentation(of: final, colorSpace: cs, options: [:]) else { return }
        let tmp = saida + ".tmp"
        try? jpg.write(to: URL(fileURLWithPath: tmp))
        rename(tmp, saida)
    }
}

let sessao = AVCaptureSession()
sessao.addInput(try! AVCaptureDeviceInput(device: disp))
let vo = AVCaptureVideoDataOutput()
vo.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
let gravador = Gravador()
vo.setSampleBufferDelegate(gravador, queue: DispatchQueue(label: "quadros"))
sessao.addOutput(vo)
NotificationCenter.default.addObserver(forName: AVCaptureDevice.wasDisconnectedNotification, object: disp, queue: nil) { _ in
    FileHandle.standardError.write("iPhone desconectado do cabo\n".data(using: .utf8)!); exit(3)
}
sessao.startRunning()
RunLoop.main.run()
