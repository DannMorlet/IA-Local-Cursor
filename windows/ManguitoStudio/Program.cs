using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Web.WebView2.WinForms;
using Microsoft.Web.WebView2.Core;

namespace ManguitoStudio;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new StudioWindow());
    }
}

public sealed class StudioWindow : Form
{
    private const string BaseUrl = "http://127.0.0.1:8765/";
    private readonly WebView2 web = new() { Dock = DockStyle.Fill };
    private Process? backend;
    private string? token;

    public StudioWindow()
    {
        Text = "Manguito Studio · IA Local";
        BackColor = Color.FromArgb(11, 16, 23);
        ForeColor = Color.White;
        MinimumSize = new Size(900, 650);
        Size = new Size(1440, 900);
        StartPosition = FormStartPosition.CenterScreen;
        Controls.Add(web);
        Shown += async (_, _) => await StartAsync();
        FormClosing += (_, _) => StopBackend();
    }

    private async Task StartAsync()
    {
        var sidecar = Path.Combine(AppContext.BaseDirectory, "Manguito-Backend.exe");
        if (!File.Exists(sidecar))
        {
            MessageBox.Show(this,
                "No se encontró Manguito-Backend.exe junto al programa.\n" +
                "Extrae TODOS los archivos del ZIP antes de ejecutarlo.",
                "Manguito Studio · Instalación incompleta", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        // No conectarse a otro servicio que ya ocupe el mismo puerto.
        try
        {
            using var tcp = new System.Net.Sockets.TcpClient();
            var check = tcp.ConnectAsync("127.0.0.1", 8765);
            if (await Task.WhenAny(check, Task.Delay(250)) == check && tcp.Connected)
            {
                MessageBox.Show(this, "El puerto local 8765 ya está ocupado.\n" +
                    "Cierra otras instancias de Manguito antes de abrir esta.",
                    "Manguito Studio", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
        }
        catch (System.Net.Sockets.SocketException) { /* Puerto libre */ }

        token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
        string folder = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Manguito", "Workspace");
        Directory.CreateDirectory(folder);
        var start = new ProcessStartInfo(sidecar)
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            WorkingDirectory = AppContext.BaseDirectory,
            WindowStyle = ProcessWindowStyle.Hidden
        };
        start.Environment["MANGUITO_TOKEN"] = token;
        start.Environment["MANGUITO_WORKSPACE"] = folder;
        start.Environment["MANGUITO_MODEL_URL"] = "http://127.0.0.1:1234/v1";
        start.Environment["MANGUITO_ENABLE_WRITES"] = "0";
        try
        {
            backend = Process.Start(start);
            if (backend is null) throw new InvalidOperationException("No se pudo iniciar Manguito Backend");

            bool ready = false;
            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
            for (int attempt = 0; attempt < 40 && !IsDisposed; attempt++)
            {
                if (backend.HasExited) break;
                try
                {
                    using var request = new HttpRequestMessage(HttpMethod.Get, BaseUrl + "v1/status");
                    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                    using var response = await client.SendAsync(request);
                    if (response.IsSuccessStatusCode) { ready = true; break; }
                }
                catch (HttpRequestException) { }
                catch (TaskCanceledException) { }
                await Task.Delay(250);
            }
            if (!ready)
                throw new InvalidOperationException("El servidor local no arrancó. Comprueba el antivirus y el puerto 8765.");

            await web.EnsureCoreWebView2Async();
            var core = web.CoreWebView2;
            core.Settings.AreDevToolsEnabled = false;
            core.Settings.AreDefaultContextMenusEnabled = false;
            core.NavigationStarting += (_, args) =>
            {
                if (!args.Uri.StartsWith(BaseUrl, StringComparison.OrdinalIgnoreCase))
                    args.Cancel = true;
            };
            core.NewWindowRequested += (_, args) => args.Handled = true;
            string payload = JsonSerializer.Serialize(token);
            await core.AddScriptToExecuteOnDocumentCreatedAsync(
                "try { sessionStorage.setItem('manguito_token', " + payload + "); } catch (e) {}");
            web.Source = new Uri(BaseUrl);
        }
        catch (Exception ex)
        {
            StopBackend();
            MessageBox.Show(this, ex.Message + "\n\nManguito.exe original no ha sido modificado.",
                "Manguito Studio · No disponible", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void StopBackend()
    {
        if (backend is null) return;
        try
        {
            if (!backend.HasExited) backend.Kill(entireProcessTree: true);
        }
        catch (InvalidOperationException) { }
        catch (System.ComponentModel.Win32Exception) { }
        backend.Dispose();
        backend = null;
    }
}
