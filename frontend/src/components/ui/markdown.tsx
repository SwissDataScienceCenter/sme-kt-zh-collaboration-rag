import React, { FunctionComponent } from "react";
import ReactMarkdown from "react-markdown";
import RemarkMath from "remark-math";
import RemarkBreaks from "remark-breaks";
import RehypeKatex from "rehype-katex";
import RemarkGfm from "remark-gfm";
import RehypeHighlight from "rehype-highlight";
import RehypeSanitize from "rehype-sanitize";
import RehypeRaw from "rehype-raw";
import { cn } from "@/lib/lorem";

export const Markdown: FunctionComponent<{ content: string }> = ({ content }) => (
    <ReactMarkdown
        remarkPlugins={[RemarkMath, RemarkGfm, RemarkBreaks]}
        rehypePlugins={[
            RehypeKatex,
            RehypeRaw,
            RehypeSanitize,
            [
                RehypeHighlight,
                {
                    detect: false,
                    ignoreMissing: true,
                },
            ],
        ]}
        components={{
            h1: ({ node, ...props }) => <h1 className="text-3xl font-bold my-4 text-foreground" {...props} />,
            h2: ({ node, ...props }) => <h2 className="text-2xl font-bold my-3 text-foreground" {...props} />,
            h3: ({ node, ...props }) => <h3 className="text-xl font-bold my-2 text-foreground" {...props} />,
            h4: ({ node, ...props }) => <h4 className="text-lg font-semibold my-1 text-foreground" {...props} />,
            h5: ({ node, ...props }) => <h5 className="text-base font-semibold my-1 text-foreground" {...props} />,
            h6: ({ node, ...props }) => <h6 className="text-sm font-semibold my-1 text-foreground" {...props} />,
            p: (pProps) => <p {...pProps} className={cn(pProps.className, "mb-2 leading-relaxed text-foreground")} dir="auto" />,
            a: (aProps) => {
                const href = aProps.href || "";
                const isInternal = /^\/#/i.test(href);
                const target = isInternal ? "_self" : aProps.target ?? "_blank";
                return (
                    <a
                        {...aProps}
                        href={href}
                        target={target}
                        rel="noopener noreferrer"
                        className={cn(aProps.className, "text-blue-500 hover:text-blue-600 hover:underline")}
                    />
                );
            },
            code: (codeProps: any) => {
                const { inline, className: codeClass, children, ...props } = codeProps;
                if (inline) {
                    return (
                        <code {...props} className={cn(codeClass, "bg-code-background text-code text-sm p-1 rounded")}>
                            {children}
                        </code>
                    );
                } else {
                    return (
                        <pre className={cn(codeClass, "bg-code-background text-code text-sm p-2 rounded-md overflow-auto my-2")}>
                            <code {...props} className={codeClass}>
                                {children}
                            </code>
                        </pre>
                    );
                }
            },
            pre: (preProps) => (
                <pre {...preProps} className={cn(preProps.className, "bg-code-background text-code text-sm p-4 my-4 rounded-md overflow-auto")} />
            ),
            blockquote: (bqProps) => <blockquote {...bqProps} className="border-l-4 border-gray-300 pl-4 italic my-4 text-gray-600" />,
            hr: () => <hr className="my-4 border-t border-border" />,
            ul: (ulProps) => <ul {...ulProps} className="list-disc list-inside my-2 text-foreground" />,
            ol: (olProps) => <ol {...olProps} className="list-decimal list-inside my-2 text-foreground" />,
            li: (liProps) => <li {...liProps} className="ml-4 text-foreground my-1" />,
            input: ({ node, ...props }) => <input {...props} disabled className="mr-2 cursor-not-allowed" />,
            strong: ({ node, ...props }) => <strong {...props} className="font-semibold text-foreground" />,
            em: ({ node, ...props }) => <em {...props} className="italic text-foreground" />,
            del: ({ node, ...props }) => <del {...props} className="line-through text-foreground" />,
            // @ts-ignore
            table: (tableProps) => <table {...tableProps} className="w-full border-collapse border border-border my-4 text-foreground" />,
            thead: (theadProps) => <thead {...theadProps} className="bg-background text-foreground" />,
            tbody: (tbodyProps) => <tbody {...tbodyProps} className="text-foreground" />,
            tr: (trProps) => <tr {...trProps} className="border border-border" />,
            th: (thProps) => <th {...thProps} className="border border-border px-3 py-2 font-semibold text-left bg-background" />,
            td: (tdProps) => <td {...tdProps} className="border border-border px-3 py-2 text-left" />,
        }}
    >
        {content}
    </ReactMarkdown>
);
