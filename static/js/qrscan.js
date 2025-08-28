// QR scanning using getUserMedia + jsQR
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const startBtn = document.getElementById('start-btn');
const scanResult = document.getElementById('scan-result');
const fileInput = document.getElementById('file-input');
const uploadResult = document.getElementById('upload-result');

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    video.srcObject = stream;
    tick();
  } catch (e) {
    scanResult.textContent = 'Camera error: ' + e.message;
  }
}

function tick() {
  if (video.readyState === video.HAVE_ENOUGH_DATA) {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imgData.data, imgData.width, imgData.height);
    if (code && code.data) {
      scanResult.innerHTML = `<a class="underline text-blue-700" href="${code.data}">${code.data}</a>`;
    }
  }
  requestAnimationFrame(tick);
}

if (startBtn) startBtn.addEventListener('click', startCamera);

if (fileInput) {
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function() {
      const img = new Image();
      img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imgData.data, imgData.width, imgData.height);
        if (code && code.data) {
          uploadResult.innerHTML = `<a class="underline text-blue-700" href="${code.data}">${code.data}</a>`;
        } else {
          uploadResult.textContent = 'No QR code found.';
        }
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}
