"use client";
import { useState, useRef } from "react";
import { Camera, Plus, X } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";

export default function RecipeSearchPage() {
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState("");
    const [showImageModal, setShowImageModal] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploadedImage, setUploadedImage] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const handleCameraClick = () => {
        setShowImageModal(true);
    };

    const handleCloseModal = () => {
        setShowImageModal(false);
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const imageUrl = URL.createObjectURL(file);
            setUploadedImage(imageUrl);
            setSelectedFile(file);
        }
    };

    const handleRemoveImage = () => {
        setUploadedImage(null);
        setSelectedFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleTextSearch = () => {
        if (!searchQuery.trim()) return;
        router.push(`/results?q=${encodeURIComponent(searchQuery)}`);
    };

    const handleSearchWithImage = async () => {
        if (!selectedFile) {
            alert("Vui lòng chọn hình ảnh trước khi tìm kiếm!");
            return;
        }
        const formData = new FormData();
        formData.append("image", selectedFile);
        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_SEARCH_API_URL}/search/image`,
                {
                    method: "POST",
                    body: formData,
                }
            );
            if (!res.ok) throw new Error("Error searching with image");
            const data = await res.json();
            localStorage.setItem("searchResults", JSON.stringify(data.results));
            router.push(`/results?img=${encodeURIComponent(uploadedImage || "")}`);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div className="flex flex-col min-h-screen">
            <main className="flex-1 flex flex-col items-center px-4">
                <div className="w-full max-w-6xl flex justify-end pt-4 pb-8">
                    <button className="bg-blue-400 hover:bg-blue-500 text-white px-4 py-2 rounded-md transition-colors">
                        Upload your recipe
                    </button>
                </div>
                <div className="text-5xl font-bold tracking-wide mb-12">
                    LOGO
                </div>
                <div className="w-full max-w-3xl relative mb-12">
                    <div className="relative w-full">
                        <input
                            type="text"
                            placeholder="Type something..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full py-4 px-5 rounded-full border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-200"
                            onKeyDown={(e) =>
                                e.key === "Enter" && handleTextSearch()
                            }
                        />
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                            <button
                                className="p-2 rounded-full hover:bg-gray-100"
                                onClick={handleCameraClick}
                            >
                                <Camera className="w-6 h-6 text-gray-500" />
                            </button>
                            <button className="p-2 rounded-full hover:bg-gray-100">
                                <Plus className="w-5 h-5 text-gray-500" />
                            </button>
                        </div>
                    </div>
                </div>
                <button
                    className="bg-gray-100 hover:bg-gray-200 px-6 py-3 rounded-md transition-colors"
                    onClick={handleTextSearch}
                >
                    Search recipe
                </button>
            </main>
            <footer className="w-full bg-gray-100 py-6 px-4 mt-auto">
                <div className="max-w-6xl mx-auto">
                    <p className="text-gray-700">Footer here</p>
                </div>
            </footer>
            {showImageModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div
                        className="absolute inset-0 bg-black/20"
                        onClick={handleCloseModal}
                    ></div>
                    <div className="relative bg-white rounded-lg w-full max-w-lg mx-4">
                        <div className="p-4 text-center border-b">
                            <h3 className="text-sm font-medium">
                                Search with image
                            </h3>
                            <button
                                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                                onClick={handleCloseModal}
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-8">
                            {!uploadedImage ? (
                                <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 flex flex-col items-center justify-center">
                                    <div className="mb-4">
                                        <svg
                                            width="40"
                                            height="40"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeWidth="2"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            className="text-gray-400"
                                        >
                                            <rect
                                                x="3"
                                                y="3"
                                                width="18"
                                                height="18"
                                                rx="2"
                                                ry="2"
                                            ></rect>
                                            <circle
                                                cx="8.5"
                                                cy="8.5"
                                                r="1.5"
                                            ></circle>
                                            <polyline points="21 15 16 10 5 21"></polyline>
                                        </svg>
                                    </div>
                                    <p className="text-sm text-gray-600">
                                        Drag and drop image here or{" "}
                                        <button
                                            onClick={handleUploadClick}
                                            className="text-blue-500 hover:underline"
                                        >
                                            upload
                                        </button>
                                    </p>
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        className="hidden"
                                        accept="image/*"
                                        onChange={handleFileChange}
                                    />
                                </div>
                            ) : (
                                <div className="flex flex-col items-center">
                                    <div className="relative w-full h-48 mb-4">
                                        <Image
                                            src={
                                                uploadedImage ||
                                                "/placeholder.svg"
                                            }
                                            alt="Uploaded image"
                                            fill
                                            className="object-contain rounded-lg"
                                        />
                                        <button
                                            onClick={handleRemoveImage}
                                            className="absolute top-2 right-2 bg-white rounded-full p-1 shadow-md hover:bg-gray-100"
                                        >
                                            <X className="w-5 h-5" />
                                        </button>
                                    </div>
                                    <button
                                        onClick={handleSearchWithImage}
                                        className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md transition-colors"
                                    >
                                        Search
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
