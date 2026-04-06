function base64urlToUint8Array(base64urlString) {
  if (!base64urlString) throw new Error("Missing base64url string");
  const padding = '='.repeat((4 - (base64urlString.length % 4)) % 4);
  const base64 = base64urlString.replace(/-/g, '+').replace(/_/g, '/') + padding;
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function addPasskey() {
  try {
    // 1️⃣ Request registration options from Flask backend
  const resp = await fetch("/authentication/passkey/register/options", { method: "POST" });
  const data = await resp.json();

  // unwrap if needed
  const publicKey = data.publicKey || data;

  publicKey.challenge = base64urlToUint8Array(publicKey.challenge);
  publicKey.user.id = base64urlToUint8Array(publicKey.user.id);

  const credential = await navigator.credentials.create({ publicKey });
  
    // 5️⃣ Convert binary response → base64
    const attestation = {
      id: credential.id,
      raw_id: btoa(String.fromCharCode(...new Uint8Array(credential.rawId))),
      type: credential.type,
      response: {
        clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(credential.response.clientDataJSON))),
        attestationObject: btoa(String.fromCharCode(...new Uint8Array(credential.response.attestationObject))),
      },
    };

    // 6️⃣ Send to backend for verification
    const verifyResp = await fetch("/authentication/passkey/register/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(attestation)
    });

    if (verifyResp.ok) {
      alert("✅ Passkey agregada correctamente");
    } else {
      const msg = await verifyResp.text();
      alert("❌ Error al registrar el Passkey: " + msg);
    }
  } catch (err) {
    console.error(err);
    alert("Error: " + err.message);
  }
}

document.getElementById("addPasskeyBtn").addEventListener("click", addPasskey);

$('#search_module').select2();
// 1. Auto-select based on URL
let currentUrl = window.location.href;
$('#search_module option').each(function () {
    let val = $(this).val();
    if (currentUrl.includes(val)) {
        $('#search_module').val(val).trigger('change.select2');
    }
});
// 2. Redirect on select
$('#search_module').on('select2:select', function (e) {
    const value = e.params.data.id;
    if (value) {
        window.location.href = `/dynamic/${value}/view`;
    }
});