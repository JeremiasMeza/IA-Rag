export default function PdfPreviewer({ fileUrl }) {
  if (!fileUrl) return null;
  return (
    <div className="mt-6 w-full flex flex-col items-center">
      <div className="mb-2 text-sm text-gray-500">Previsualización PDF</div>
      <div className="w-full max-w-3xl h-[600px] border rounded overflow-hidden bg-gray-100 shadow">
        <embed src={fileUrl} type="application/pdf" width="100%" height="100%" />
      </div>
    </div>
  );
}
