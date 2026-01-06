export function CameraView() {
    const VIDEO_URL = "http://yadiec2.freedynamicdns.net:8889/cam2";

    return (
        <div className="absolute inset-0 overflow-hidden">
            <iframe
                src={VIDEO_URL}
                title="Live Feed"
                className="absolute top-1/2 left-1/2 
                   min-w-full min-h-full 
                   -translate-x-1/2 -translate-y-1/2 
                   border-0"
                allowFullScreen
            />
        </div>
    );
}
