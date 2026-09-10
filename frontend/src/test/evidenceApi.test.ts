import {
  createEvidence,
  deleteEvidence,
  EvidenceApiError,
  getEvidence,
  listEvidence,
  presignUpload,
  uploadFile,
} from "../api/evidenceApi";

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com/prod/");
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
});

describe("evidenceApi", () => {
  it("normalizes a stage-bearing base URL with a trailing slash and sends the canonical presign payload", async () => {
    const presignResponse = {
      uploadUrl: "https://example.invalid/upload",
      assetKey: "file-key",
      expiresIn: 300,
      headers: { "Content-Type": "application/pdf" },
    };
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(presignResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const result = await presignUpload({
      fileName: "record.pdf",
      contentType: "application/pdf",
    });

    expect(result).toEqual(presignResponse);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.com/prod/uploads/presign",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          fileName: "record.pdf",
          contentType: "application/pdf",
        }),
      }),
    );
  });

  it("uses PUT for file content and POST for canonical evidence metadata", async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(null, { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "record-1" }), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        }),
      );
    const file = new File(["evidence"], "record.pdf", {
      type: "application/pdf",
    });

    await uploadFile(
      {
        uploadUrl: "https://example.invalid/upload",
        assetKey: "file-key",
        expiresIn: 300,
        headers: { "Content-Type": "application/pdf" },
      },
      file,
    );
    await createEvidence({
      title: "Professional milestone",
      tags: ["milestone"],
      fileName: file.name,
      contentType: file.type,
      assetKey: "file-key",
    });

    expect(fetchMock.mock.calls[0]).toEqual([
      "https://example.invalid/upload",
      expect.objectContaining({
        method: "PUT",
        body: file,
        headers: { "Content-Type": "application/pdf" },
      }),
    ]);
    expect(fetchMock.mock.calls[1]).toEqual([
      "https://api.example.com/prod/evidence",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          title: "Professional milestone",
          tags: ["milestone"],
          fileName: "record.pdf",
          contentType: "application/pdf",
          assetKey: "file-key",
        }),
      }),
    ]);
  });

  it("parses list and detail responses through their stable routes", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ items: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "record/1",
            assetKey: "record-1.pdf",
            assetUrl: "https://example.invalid/asset",
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );

    await expect(listEvidence()).resolves.toEqual({ items: [] });
    await expect(getEvidence("record/1")).resolves.toMatchObject({
      id: "record/1",
      assetUrl: "https://example.invalid/asset",
    });
    expect(fetchMock.mock.calls[0][0]).toBe("https://api.example.com/prod/evidence");
    expect(fetchMock.mock.calls[1][0]).toBe(
      "https://api.example.com/prod/evidence/record%2F1",
    );
  });

  it("handles an empty 204 delete response and encodes the id", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(deleteEvidence("record/1")).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.com/prod/evidence/record%2F1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("exposes canonical nested error code and message without unsafe details", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            message: "The record is invalid.",
            code: "INVALID_RECORD",
            details: { dependencyMessage: "sensitive failure" },
          },
        }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    const error = await listEvidence().catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(EvidenceApiError);
    expect(error).toMatchObject({
      name: "EvidenceApiError",
      status: 400,
      code: "INVALID_RECORD",
      message: "The record is invalid.",
    });
    expect(error).not.toHaveProperty("details");
  });

  it("uses a safe fallback for a non-JSON HTTP error", async () => {
    fetchMock.mockResolvedValue(new Response("Unavailable", { status: 503 }));

    await expect(listEvidence()).rejects.toEqual(
      expect.objectContaining({
        name: "EvidenceApiError",
        status: 503,
        message: "Request failed with status 503.",
      }),
    );
  });

  it("normalizes a browser network failure", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    const error = await listEvidence().catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(EvidenceApiError);
    expect(error).toMatchObject({ status: 0, code: "NETWORK_ERROR" });
  });
});
